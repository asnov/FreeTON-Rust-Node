import datetime
import logging
import subprocess

elector_addr = "-1:3333333333333333333333333333333333333333333333333333333333333333"
elector_addr_hex = "-1:3333333333333333333333333333333333333333333333333333333333333333"
msig_addr_hex = "0x4000610da7d7f89b92cd64212e5b983d9ccac9938333174f352a5b3c416997c4"
msig_addr = "-1:4000610da7d7f89b92cd64212e5b983d9ccac9938333174f352a5b3c416997c4"
# It stores ABIs, keys and configs like  msig.keys.json, Elector.abi.json, SafeMultisigWallet.abi.json, console.json etc
configs_dir = "/etc/rustnode"
remained_for_fees = 100

elector_type = "solidity"

logging.basicConfig(
    level=logging.INFO,
    format="DateTime : %(asctime)s : %(levelname)s : %(message)s", )


def cli_depool_config():
    depool_config = subprocess.check_output(
        'tonos-cli config --addr %s/depool.addr --wallet %s --keys %s/msig.keys.json' % (
            configs_dir, msig_addr, configs_dir), encoding='utf-8', shell=True)
    return depool_config


def get_depool_addr():
    depool_addr = subprocess.check_output('cat %s/depool.addr")' % (configs_dir), encoding='utf-8', shell=True)
    return depool_addr


def recover_query_boc():
    recover_query_boc = subprocess.check_output('base64 --wrap=0 recover-query.boc', encoding='utf-8', shell=True)
    logging.info('RECOVER QUERY BOC: %s' % recover_query_boc)
    return recover_query_boc


def cli_submit_transaction(msig_addr: str, elector_addr_hex: str, value: str, boc: str):
    trx = subprocess.check_output('tonos-cli call %s submitTransaction \
            \"{\\"dest\\":\\"%s\\",\\"value\\":\\"%s\\",\\"bounce\\":true,\\"allBalance\\":false,\\"payload\\":\\"%s\\"}\" \
            --abi %s/SafeMultisigWallet.abi.json \
            --sign %s/msig.keys.json' % (msig_addr, elector_addr_hex, value, boc, configs_dir, configs_dir),
                                  encoding='utf-8', shell=True)
    logging.info(trx)
    return trx


def cli_get_active_election_id(elector_addr: str):
    active_election_id = subprocess.check_output(
        'tonos-cli run %s active_election_id {} --abi %s/Elector.abi.json | grep value0 | awk \'{print $2}\' | tr -d \"\\"\"|tr -d \"\n\"' % (
            elector_addr, configs_dir), encoding='utf-8', shell=True)
    logging.info('ACTIVE ELECTION ID: %s' % active_election_id)
    return active_election_id


def console_create_elector_request():
    subprocess.check_output('tonos-cli getconfig 15 > global_config_15_raw', encoding='utf-8', shell=True)
    elections_end_before = subprocess.check_output(
        'cat global_config_15_raw | grep elections_end_before | awk \'{print $2}\' | tr -d \',\'', encoding='utf-8',
        shell=True)
    elections_start_before = subprocess.check_output(
        'cat global_config_15_raw | grep "elections_start_before" | awk \'{print $2}\' | tr -d \',\'', encoding='utf-8',
        shell=True)
    stake_held_for = subprocess.check_output(
        'cat global_config_15_raw | grep "stake_held_for" | awk \'{print $2}\' | tr -d \',\'', encoding='utf-8',
        shell=True)
    validators_elected_for = subprocess.check_output(
        'cat global_config_15_raw | grep "validators_elected_for" | awk \'{print $2}\' | tr -d \',\'', encoding='utf-8',
        shell=True)
    election_start = cli_get_active_election_id(elector_addr)
    election_stop = (int(election_start) + 1000 + int(elections_start_before) + int(elections_end_before) + int(
        stake_held_for) + int(validators_elected_for))

    request = subprocess.check_output(
        'console -C %s/console.json -c "election-bid %s %s"' % (configs_dir, election_start, election_stop),
        encoding='utf-8', shell=True)
    logging.info(request)


def validator_query_boc():
    validator_query_boc = subprocess.check_output('base64 --wrap=0 validator-query.boc', encoding='utf-8', shell=True)
    logging.info('VALIDATOR QUERY BOC %s' % validator_query_boc)
    return validator_query_boc


def check_validator_balance(msig_addr_hex: str):
    balance = subprocess.check_output('tonos-cli account %s | grep balance | awk \'{print $2}\'' % (msig_addr),
                                      encoding='utf-8', shell=True)
    balance_in_tokens = int(balance) / 1000000000
    logging.info('BALANCE %s' % balance_in_tokens)
    return balance_in_tokens


def get_min_stake():
    min_stake = subprocess.check_output(
        'tonos-cli getconfig 17 | grep min_stake | awk \'{print $2}\' | tr -d \'\\"\' | tr -d \',\'', encoding='utf-8',
        shell=True)
    min_stake_in_tokens = int(min_stake) / 1000000000
    logging.info('MIN STAKE %s' % min_stake_in_tokens)
    return min_stake_in_tokens


def get_stake():
    actual_balance = check_validator_balance(msig_addr_hex)
    stake = (actual_balance - remained_for_fees) / 2
    logging.info('WILL BE STAKED %s' % stake)
    return stake


def submit_stake():
    stake = get_stake()
    nanostake = subprocess.check_output('tonos-cli convert tokens %s | tail -1' % (int(stake)), encoding='utf-8',
                                        shell=True)
    boc = validator_query_boc();
    depool_addr = get_depool_addr()
    trx = cli_submit_transaction(msig_addr, depool_addr, int(nanostake), boc)
    logging.info(trx)
    return trx


def cli_get_active_election_id():
    if elector_type == 'solidity':
        active_election_id_hex = subprocess.check_output(
            'tonos-cli run %s active_election_id {} --abi %s/Elector.abi.json | grep value0 | awk \'{print $2}\' | tr -d \'"\'' % (
                elector_addr, configs_dir), encoding='utf-8', shell=True)
        return active_election_id_hex
    if elector_type == 'fift':
        active_election_id_hex = subprocess.check_output(
            'tonos-cli runget %s active_election_id | grep Result: | awk -F \'\\"\' \'{print $2}\' ' % (
                elector_addr), encoding='utf-8', shell=True)
        return active_election_id_hex


def cli_get_active_election_id_from_depool_event():
    subprocess.check_output(
        'tonos-cli depool --addr %s/depool.addr events > %s/events.txt 2>&1' % (
            configs_dir, configs_dir), encoding='utf-8', shell=True)
    active_election_id_from_depool_event = subprocess.check_output(
        'grep \\"^{\\" \\ %s/events.txt | grep electionId |jq \".electionId\" | head -1 | tr -d \'"\' | xargs printf "%d\n" ' % (
            elector_addr), encoding='utf-8', shell=True)
    active_election_id = cli_get_active_election_id()
    if active_election_id_from_depool_event == active_election_id:
        proxy_addr_from_depool_event = subprocess.check_output(
            'grep \\"^{\\" \\ %s/events.txt | grep electionId |jq \".proxy\" | head -1 | tr -d \'"\' | xargs printf "%d\n" ' % (
                elector_addr), encoding='utf-8', shell=True)
        return proxy_addr_from_depool_event


try:
    cli_depool_config()
    if cli_get_active_election_id():
        console_create_elector_request()
        submit_stake()
except:
    logging.info('ERROR')